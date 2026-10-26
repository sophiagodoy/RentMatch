"""Regressões da limpeza e da entrada usada pelos modelos."""
import io
import unittest

import numpy as np
import pandas as pd

from candidatos import construir_candidatos
import config_modelo as cfg
from preparo import carregar_csv, limpar, montar_entrada, montar_grupos, dobras_cv


class TestPreparo(unittest.TestCase):
    def dados(self, n=30):
        return pd.DataFrame({
            "id_anuncio": [str(i) for i in range(n)],
            "bairro": " Cambuí ", "tipo": "apartamento",
            "area_m2": 50., "aluguel": np.linspace(1000, 2000, n),
            "quartos": 2., "vagas": 1., "taxas": 100.,
        })

    def test_csv_preserva_identificadores(self):
        df = carregar_csv(io.StringIO("id_anuncio,aluguel,area_m2\n001,1200,50\n"))
        self.assertEqual(df.id_anuncio.iloc[0], "001")

    def test_duplicados_datas_e_ids_ausentes(self):
        df = self.dados(4)
        df["id_anuncio"] = [" 1 ", "1", None, ""]
        df["atualizado_em"] = ["2026-01-01", "invalida", None, None]
        limpo, rel = limpar(df)
        self.assertEqual(len(limpo), 3)
        self.assertEqual(rel["duplicados_removidos"], 1)
        self.assertEqual(limpo.loc[limpo.id_anuncio == "1", "aluguel"].iloc[0], 1000)
        self.assertEqual(len(set(montar_grupos(limpo))), 3)

    def test_cidade_e_normalizacao(self):
        df = self.dados(4)
        df["endereco_completo"] = ["Rua A · Campinas", "Rua A · Valinhos", None, "Rua B"]
        limpo, rel = limpar(df)
        self.assertEqual(rel["fora_da_cidade"], 1)
        self.assertEqual(len(limpo), 3)
        self.assertEqual(set(limpo.bairro), {"cambui"})

    def test_numeros_invalidos_e_colunas_obrigatorias(self):
        df = self.dados(4).astype({"aluguel": object})
        df["aluguel"] = ["1200", "erro", np.inf, 2000]
        df["quartos"] = [-1, 2, 2, 1.5]
        df["taxas"] = [np.inf, 0, 0, -10]
        limpo, rel = limpar(df)
        self.assertEqual(rel["fora_das_faixas_ou_sem_dados"], 2)
        self.assertTrue(limpo.quartos.isna().all())
        self.assertTrue(limpo.taxas.isna().all())
        with self.assertRaisesRegex(ValueError, "area_m2"):
            limpar(df.drop(columns="area_m2"))

    def test_extremos_validos_preservados_por_padrao(self):
        df = self.dados()
        df.loc[0, "aluguel"] = 90000
        limpo, rel = limpar(df)
        self.assertEqual(len(limpo), len(df))
        self.assertEqual(rel["outliers_removidos"], 0)
        exploracao, _ = limpar(df, outlier_z=4)
        self.assertLess(len(exploracao), len(df))

    def test_grupos_normalizam_endereco_e_nao_unem_ausentes(self):
        df = self.dados(4)
        df["endereco_completo"] = [" Rua Á ", "rua a", None, ""]
        grupos = montar_grupos(df)
        self.assertEqual(grupos[0], grupos[1])
        self.assertNotEqual(grupos[2], grupos[3])

    def test_alvo_constante_e_poucos_grupos(self):
        y = pd.Series([1000.] * 30)
        grupos = np.repeat(np.arange(15), 2)
        for treino, teste in dobras_cv(y, grupos):
            self.assertTrue(set(grupos[treino]).isdisjoint(grupos[teste]))
            self.assertGreater(len(teste), 0)
        with self.assertRaisesRegex(ValueError, "grupos suficientes"):
            dobras_cv(y, np.zeros(30))

    def test_formulario_rejeita_nao_finitos_e_contagens_fracionarias(self):
        dados = self.dados(1).iloc[0].to_dict()
        for campo, valor in [("area_m2", "nan"), ("taxas", "inf"),
                             ("quartos", 1.5), ("vagas", -1)]:
            with self.subTest(campo=campo), self.assertRaises(ValueError):
                montar_entrada({**dados, campo: valor})

    def test_candidatos_com_colunas_opcionais_totalmente_ausentes(self):
        df, _ = limpar(self.dados().drop(columns=["taxas", "quartos", "vagas"]))
        for nome, modelo in construir_candidatos().items():
            with self.subTest(modelo=nome):
                modelo.fit(df.drop(columns="aluguel"), df.aluguel)
                self.assertTrue(np.isfinite(modelo.predict(df.iloc[:2])).all())

    def test_limites_permitidos_na_limpeza_e_no_formulario(self):
        base = self.dados(1)
        limites = {
            "area_m2": (cfg.AREA_MIN, cfg.AREA_MAX),
            "aluguel": (cfg.ALUGUEL_MIN, cfg.ALUGUEL_MAX),
            "quartos": (0, 20), "vagas": (0, 20),
        }
        for campo, (minimo, maximo) in limites.items():
            for valor in (minimo, maximo):
                with self.subTest(campo=campo, limite=valor):
                    dados = base.assign(**{campo: float(valor)})
                    limpo, _ = limpar(dados)
                    self.assertEqual(len(limpo), 1)
                    self.assertEqual(limpo[campo].iloc[0], valor)
                    if campo != cfg.ALVO:
                        entrada = montar_entrada(dados.iloc[0].to_dict())
                        self.assertEqual(entrada[campo].iloc[0], valor)
            for valor in (minimo - 1, maximo + 1):
                with self.subTest(campo=campo, fora=valor):
                    dados = base.assign(**{campo: float(valor)})
                    limpo, _ = limpar(dados)
                    if campo in (cfg.ALVO, "area_m2"):
                        self.assertTrue(limpo.empty)
                    else:
                        self.assertEqual(len(limpo), 1)
                        self.assertTrue(pd.isna(limpo[campo].iloc[0]))
                    if campo != cfg.ALVO:
                        with self.assertRaises(ValueError):
                            montar_entrada(dados.iloc[0].to_dict())


if __name__ == "__main__":
    unittest.main()
