"""Verifica a persistência do artefato produzido pelo treinamento."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import joblib
import numpy as np
import pandas as pd

import treinar
from preparo import montar_entrada


class TestTreino(unittest.TestCase):
    def test_modelo_salvo_preserva_previsoes_e_metadados(self):
        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta)
            csv = pasta / "dados.csv"
            saida = pasta / "artefatos"
            indice = np.arange(120)
            pd.DataFrame({
                "id_anuncio": [f"anuncio-{i}" for i in indice],
                "bairro": "Cambuí", "tipo": "apartamento",
                "area_m2": 40 + indice, "quartos": 1 + indice % 3,
                "vagas": indice % 2, "taxas": 100 + indice,
                "aluguel": 900 + 20 * indice,
            }).to_csv(csv, index=False)
            entrada = montar_entrada({
                "bairro": "Cambuí", "tipo": "apartamento", "area_m2": 65,
                "quartos": 2, "vagas": 1, "condominio": 100, "iptu": 20,
            })
            antes = []
            gravar = joblib.dump

            def registrar_e_gravar(artefato, caminho):
                antes.append(artefato["modelo"].predict(entrada).copy())
                return gravar(artefato, caminho)

            with patch.object(treinar.joblib, "dump", side_effect=registrar_e_gravar):
                meta = treinar.executar(csv=csv, saida=saida, candidatos=["ridge"],
                                       min_linhas=30, verboso=False)

            self.assertEqual(len(antes), 1)
            self.assertTrue(np.isfinite(antes[0]).all())
            self.assertTrue((antes[0] > 0).all())
            for versao in (meta["versao"], "atual"):
                with self.subTest(versao=versao):
                    artefato = joblib.load(saida / f"modelo_{versao}.joblib")
                    np.testing.assert_allclose(artefato["modelo"].predict(entrada),
                                               antes[0], rtol=1e-12, atol=1e-12)
                    self.assertEqual(artefato["meta"], meta)
                    salvo = json.loads((saida / f"metadados_{versao}.json").read_text(
                        encoding="utf-8"))
                    self.assertEqual(salvo, meta)


if __name__ == "__main__":
    unittest.main()
