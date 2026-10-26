"""Verifica os limites da validação: dobras, grupos e teste reservado."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin

import config_modelo as cfg
import validar
from preparo import carregar_csv, limpar, montar_grupos, separar_treino_teste


class RegressorEspiao(RegressorMixin, BaseEstimator):
    """Registra quais imóveis cada ajuste/previsão recebeu."""
    ajustes = []
    previsoes = []

    def fit(self, X, y):
        self.areas_ = set(X["area_m2"])
        self.media_ = float(np.mean(y))
        type(self).ajustes.append(self.areas_)
        return self

    def predict(self, X):
        areas = set(X["area_m2"])
        if self.areas_ & areas:
            raise AssertionError("O grupo usado para prever já participou deste ajuste.")
        type(self).previsoes.append(areas)
        return np.full(len(X), self.media_)


class TestValidacao(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pasta = Path(self.tmp.name)
        self.csv = self.pasta / "dados.csv"
        # Duas linhas por grupo, com área única por grupo para auditar os ajustes.
        grupo = np.repeat(np.arange(60), 2)
        pd.DataFrame({
            "id_anuncio": [f"anuncio-{i}" for i in range(len(grupo))],
            "endereco_completo": [f"Rua {g}" for g in grupo],
            "bairro": [f"bairro-{g % 4}" for g in grupo],
            "tipo": "apartamento", "area_m2": 40 + grupo,
            "quartos": 1 + grupo % 3, "vagas": grupo % 2, "taxas": 100 + 5 * grupo,
            "aluguel": (40 + grupo) * 20 + 100 * (grupo % 4),
        }).to_csv(self.csv, index=False)
        self.saida = self.pasta / "relatorios"
        RegressorEspiao.ajustes = []
        RegressorEspiao.previsoes = []

    def executar(self, **opcoes):
        return validar.executar(csv=self.csv, saida=self.saida, min_linhas=30, verboso=False, **opcoes)

    def test_holdout_e_grupos_nao_entram_nos_ajustes_ou_previsoes(self):
        df, _ = limpar(carregar_csv(self.csv))
        grupos = montar_grupos(df)
        i_tr, i_te = separar_treino_teste(df[cfg.ALVO], grupos)
        areas_teste = set(df.iloc[i_te].area_m2)
        self.saida.mkdir()
        modelo_existente = self.saida / "modelo_atual.joblib"
        modelo_existente.write_bytes(b"modelo existente")
        with patch.object(validar, "construir_candidatos", return_value={"baseline": RegressorEspiao()}):
            rel = self.executar()
        self.assertEqual(len(RegressorEspiao.ajustes), cfg.N_FOLDS_CV)
        self.assertEqual(len(RegressorEspiao.previsoes), cfg.N_FOLDS_CV)
        for areas in RegressorEspiao.ajustes + RegressorEspiao.previsoes:
            self.assertTrue(areas.isdisjoint(areas_teste))
        self.assertEqual(set.union(*RegressorEspiao.previsoes), set(df.iloc[i_tr].area_m2))
        self.assertEqual(rel["divisao"]["indices_treino"], i_tr.tolist())
        self.assertEqual(rel["divisao"]["indices_teste_reservado"], i_te.tolist())
        self.assertFalse(rel["teste_avaliado"])
        self.assertFalse(rel["modelo_final_treinado"])
        self.assertEqual(modelo_existente.read_bytes(), b"modelo existente")
        self.assertEqual(list(self.saida.glob("*.joblib")), [modelo_existente])

    def test_modelos_reais_relatorios_e_metricas_por_dobra(self):
        rel = self.executar(candidatos=["baseline", "ridge"])
        comparacao = pd.read_csv(self.saida / "resultados_validacao.csv", index_col="modelo")
        dobras = pd.read_csv(self.saida / "metricas_por_dobra.csv")
        previsoes = pd.read_csv(self.saida / "previsoes_validacao.csv")
        salvo = json.loads((self.saida / "relatorio_validacao.json").read_text(encoding="utf-8"))
        self.assertEqual(len(dobras), 2 * cfg.N_FOLDS_CV)
        self.assertEqual(len(previsoes), rel["divisao"]["linhas_treino"])
        self.assertEqual(previsoes.indice_csv_limpo.nunique(), len(previsoes))
        self.assertEqual(previsoes.groupby("grupo").dobra.nunique().max(), 1)
        self.assertTrue(np.isfinite(comparacao[validar.METRICAS].to_numpy()).all())
        self.assertEqual(comparacao.index[0], rel["modelo_escolhido"])
        for nome, m in rel["cv_treino"].items():
            segmento = dobras[dobras.modelo == nome]
            self.assertEqual(segmento.n.sum(), m["n"])
            self.assertAlmostEqual(np.average(segmento.mae, weights=segmento.n), m["mae"], places=5)
        escolhido = rel["cv_treino"][rel["modelo_escolhido"]]
        self.assertAlmostEqual(previsoes.erro_reais.abs().mean(), escolhido["mae"], places=5)
        self.assertEqual(salvo, rel)
        analise = (self.saida / "analise_validacao.md").read_text(encoding="utf-8")
        self.assertIn(f"**{rel['modelo_escolhido']}**", analise)
        self.assertIn(validar.LIMITACOES[0], analise)

    def test_repeticao_preserva_divisao_e_resultados(self):
        primeira = self.executar(candidatos=["baseline"])
        segunda = self.executar(candidatos=["baseline"])
        self.assertEqual(primeira["divisao"], segunda["divisao"])
        self.assertEqual(primeira["cv_treino"], segunda["cv_treino"])

    def test_entradas_invalidas_falham_antes_de_gravar_relatorios(self):
        for candidatos in [[], ["inexistente"]]:
            with self.subTest(candidatos=candidatos), self.assertRaisesRegex(ValueError, "candidatos válidos"):
                self.executar(candidatos=candidatos)
        with patch.object(cfg, "FEATURES", cfg.FEATURES + [cfg.ALVO]):
            with self.assertRaisesRegex(ValueError, "derivada do alvo"):
                self.executar()
        with self.assertRaisesRegex(ValueError, "mínimo 300"):
            validar.executar(csv=self.csv, saida=self.saida, verboso=False)
        self.assertFalse(self.saida.exists())

    def test_csv_vazio_ou_sem_imoveis_validos(self):
        original = pd.read_csv(self.csv)
        casos = {
            "sem_conteudo": "",
            "somente_cabecalho": original.iloc[:0].to_csv(index=False),
            "todos_invalidos": original.assign(aluguel=-1).to_csv(index=False),
        }
        for nome, conteudo in casos.items():
            with self.subTest(caso=nome):
                self.csv.write_text(conteudo, encoding="utf-8")
                if nome == "sem_conteudo":
                    with self.assertRaises(pd.errors.EmptyDataError):
                        self.executar(candidatos=["baseline"])
                else:
                    limpo, rel = limpar(carregar_csv(self.csv))
                    self.assertTrue(limpo.empty)
                    self.assertEqual(rel["linhas_finais"], 0)
                    with self.assertRaisesRegex(ValueError, "Só 0 imóveis"):
                        self.executar(candidatos=["baseline"])
                self.assertFalse(self.saida.exists())


if __name__ == "__main__":
    unittest.main()
