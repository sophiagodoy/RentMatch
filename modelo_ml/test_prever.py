"""Contrato de previsão, classificação e explicação usado pelo backend."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import joblib
import numpy as np
import pandas as pd

from candidatos import construir_candidatos
from preparo import montar_entrada
from prever import avaliar_imovel, carregar_modelo


class TestPrever(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pasta = tempfile.TemporaryDirectory()
        cls.caminho = Path(cls.pasta.name) / "modelo.joblib"
        indice = np.arange(60)
        cls.fundo = pd.DataFrame({
            "bairro": "cambui", "tipo": "apartamento", "area_m2": 30 + indice,
            "quartos": 1 + indice % 3, "vagas": indice % 2, "taxas": 100 + indice
        })
        cls.modelo = construir_candidatos()["ridge"].fit(cls.fundo, 800 + 20 * indice)
        joblib.dump({"modelo": cls.modelo, "fundo": cls.fundo.iloc[:8],
                     "intervalo_erro": (-0.1, 0.2), "meta": {"versao": "teste"}}, cls.caminho)
        cls.dados = {"bairro": "Cambuí", "tipo": "Apartamento", "area_m2": 65,
                     "quartos": 2, "vagas": 1, "condominio": 100, "iptu": 20,
                     "valor_anunciado": 1800}

    @classmethod
    def tearDownClass(cls):
        carregar_modelo.cache_clear()
        cls.pasta.cleanup()

    def test_resultado_vem_do_modelo_e_nao_do_valor_anunciado(self):
        resultado = avaliar_imovel(self.dados, caminho=self.caminho)
        esperado = round(float(self.modelo.predict(montar_entrada(self.dados))[0]), 2)
        self.assertEqual(resultado["valor_estimado"], esperado)
        barato = avaliar_imovel({**self.dados, "valor_anunciado": esperado * 0.5}, caminho=self.caminho)
        caro = avaliar_imovel({**self.dados, "valor_anunciado": esperado * 2}, caminho=self.caminho)
        self.assertEqual(barato["valor_estimado"], caro["valor_estimado"])
        self.assertEqual(barato["classificacao"], "Oportunidade")
        self.assertEqual(caro["classificacao"], "Caro")
        self.assertEqual(resultado["versao_modelo"], "teste")
        self.assertEqual(len(resultado["fatores"]), 4)
        self.assertTrue(all("valor_informado" in fator for fator in resultado["fatores"]))
        self.assertLess(resultado["intervalo_estimado"][0], esperado)
        self.assertGreater(resultado["intervalo_estimado"][1], esperado)
        json.dumps(resultado, allow_nan=False)

    def test_taxas_ausentes_e_bairro_desconhecido_geram_resultado_com_aviso(self):
        resultado = avaliar_imovel({**self.dados, "bairro": "Bairro novo", "condominio": None, "iptu": None},
                                   caminho=self.caminho)
        self.assertGreater(resultado["valor_estimado"], 0)
        self.assertTrue(resultado["avisos"])
        json.dumps(resultado, allow_nan=False)

    def test_entrada_invalida_e_modelo_ausente_nao_geram_resultado(self):
        for alteracao in ({"quartos": 1.5}, {"area_m2": 0}, {"valor_anunciado": float("nan")}, {"valor_anunciado": 0}):
            with self.subTest(alteracao=alteracao), self.assertRaises(ValueError):
                avaliar_imovel({**self.dados, **alteracao}, caminho=self.caminho)
        with self.assertRaises(FileNotFoundError):
            avaliar_imovel(self.dados, caminho=Path(self.pasta.name) / "ausente.joblib")

    def test_json_por_stdin_preserva_acentos_e_codigo_de_erro(self):
        script = str(Path(__file__).with_name("prever.py"))
        for entrada, caminho, codigo in ((json.dumps(self.dados), self.caminho, 0),
                                         ("{invalido", self.caminho, 1),
                                         (json.dumps(self.dados), Path(self.pasta.name) / "ausente", 2)):
            with self.subTest(codigo=codigo):
                processo = subprocess.run([sys.executable, "-X", "utf8", script, "--json", "--modelo", str(caminho)],
                                          input=entrada, text=True, encoding="utf-8", capture_output=True, timeout=20)
                self.assertEqual(processo.returncode, codigo, processo.stderr)
                resposta = json.loads(processo.stdout)
                self.assertIn("valor_estimado" if codigo == 0 else "erro", resposta)


if __name__ == "__main__":
    unittest.main()
