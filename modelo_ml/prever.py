"""Avaliação de imóveis com o artefato treinado e explicações de Shapley."""
import argparse
from functools import lru_cache
import json
import math
from pathlib import Path
import sys

import joblib

import config_modelo as cfg
from classificador import classificar
from explicador import fatores_para_usuario, valores_shapley
from preparo import montar_entrada


@lru_cache(maxsize=2)
def carregar_modelo(caminho):
    caminho = Path(caminho)
    if not caminho.is_file():
        raise FileNotFoundError("Modelo não treinado. Execute python modelo_ml/treinar.py.")
    return joblib.load(caminho)


def avaliar_imovel(dados, valor_anunciado=None, caminho=None):
    if not isinstance(dados, dict):
        raise ValueError("Informe um objeto com os dados do imóvel.")
    entrada = montar_entrada(dados)
    try:
        anunciado = float(valor_anunciado if valor_anunciado is not None
                          else dados.get("valor_anunciado", dados.get("anunciado")))
    except (TypeError, ValueError):
        raise ValueError("Informe um valor anunciado válido.") from None
    if not math.isfinite(anunciado) or anunciado <= 0:
        raise ValueError("O valor anunciado deve ser maior que zero.")

    artefato = carregar_modelo(str(caminho or cfg.ARTEFATOS_DIR / "modelo_atual.joblib"))
    modelo = artefato["modelo"]
    estimado = float(modelo.predict(entrada)[0])
    if not math.isfinite(estimado) or estimado <= 0:
        raise ValueError("Não foi possível estimar este imóvel.")
    explicacao = valores_shapley(modelo, entrada, artefato["fundo"])
    baixo, alto = artefato["intervalo_erro"]
    intervalo = [round(max(0.01, estimado * (1 + erro)), 2) for erro in (baixo, alto)]
    estimado = round(estimado, 2)

    avisos = []
    pipeline = getattr(modelo, "regressor_", modelo)
    agrupador = pipeline.named_steps.get("agrupar")
    for campo, label in (("bairro", "Bairro"), ("tipo", "Tipo de imóvel")):
        frequentes = getattr(agrupador, "frequentes_", {}).get(campo)
        if frequentes is not None and entrada[campo].iloc[0] not in frequentes:
            avisos.append(f"{label} pouco representado nos dados; a estimativa usa um agrupamento de imóveis.")

    return {
        "valor_estimado": estimado,
        "valor_anunciado": round(anunciado, 2),
        "intervalo_estimado": intervalo,
        **classificar(anunciado, estimado),
        "fatores": fatores_para_usuario(explicacao, entrada),
        "valor_base": round(explicacao["base"], 2),
        "avisos": avisos,
        "versao_modelo": artefato["meta"]["versao"],
    }


def main():
    parser = argparse.ArgumentParser(description="Avalia um aluguel com o modelo RentMatch.")
    parser.add_argument("--json", action="store_true", help="Lê um objeto JSON pelo stdin.")
    parser.add_argument("--modelo", type=Path)
    parser.add_argument("--bairro")
    parser.add_argument("--tipo")
    parser.add_argument("--area", type=float)
    parser.add_argument("--quartos", type=int)
    parser.add_argument("--vagas", type=int)
    parser.add_argument("--condominio", type=float)
    parser.add_argument("--iptu", type=float)
    parser.add_argument("--anunciado", type=float)
    args = parser.parse_args()
    try:
        dados = json.load(sys.stdin) if args.json else {
            "bairro": args.bairro, "tipo": args.tipo, "area_m2": args.area,
            "quartos": args.quartos, "vagas": args.vagas,
            "condominio": args.condominio, "iptu": args.iptu, "anunciado": args.anunciado
        }
        resultado = avaliar_imovel(dados, caminho=args.modelo)
        print(json.dumps(resultado, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, TypeError) as error:
        print(json.dumps({"erro": str(error)}, ensure_ascii=False))
        return 1
    except (FileNotFoundError, KeyError, OSError):
        print(json.dumps({"erro": "Modelo indisponível. Execute o treinamento antes de avaliar."}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
