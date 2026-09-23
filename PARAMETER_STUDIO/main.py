#!/usr/bin/env python3
"""
Script para varrer o diretório de catálogos (catalogs_full), identificar os
models que contêm "_CM_" no nome, localizar os 3 XMLs (client, oss, operations)
de cada versão e encontrar a planilha de documentação correspondente em
C:\\PARAMETER_STUDIO\\Mapeamento_Catalogos.

MODOS DE EXECUÇÃO
-----------------
1) Varredura completa (padrão, sem argumentos):
       python script.py

2) Manual via linha de comando (processa só o que for passado):
       python script.py --client C:\\...\\X_client.xml --oss C:\\...\\X_oss.xml ^
                        --operations C:\\...\\X_operations.xml --documentacao C:\\...\\Mapeamento.xlsx

3) Manual via lista no script (preencha CATALOGOS_MANUAIS e rode):
       python script.py --manual
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

from altera_catalogo import articulador

# ---------------------------------------------------------------------------
# CONFIGURAÇÕES - ajuste os caminhos se necessário
# ---------------------------------------------------------------------------
CATALOGS_ROOT = Path(r"C:\Altaia\Vivo\GITHUB\altaia-vivo-namf-sol\automation-vivo\catalogs_full")
MAPPING_ROOT = Path(r"C:\PARAMETER_STUDIO\Mapeamento_Catalogos")

# Sufixos dos XMLs que precisamos localizar dentro de cada pasta de versão
XML_SUFFIXES = {
    "client": "_client.xml",
    "oss": "_oss.xml",
    "operations": "_operations.xml",
}

# ---------------------------------------------------------------------------
# CATÁLOGOS MANUAIS - usados com "--manual".
# Adicione um dicionário por catálogo que você quer alterar.
# ---------------------------------------------------------------------------
CATALOGOS_MANUAIS = [
    # {
    #     "client":       r"C:\...\ERICSSON\MODEL_CM_X\23.Q4\MODEL_CM_X_client.xml",
    #     "oss":          r"C:\...\ERICSSON\MODEL_CM_X\23.Q4\MODEL_CM_X_oss.xml",
    #     "operations":   r"C:\...\ERICSSON\MODEL_CM_X\23.Q4\MODEL_CM_X_operations.xml",
    #     "documentacao": r"C:\PARAMETER_STUDIO\Mapeamento_Catalogos\Ericsson\Mapeamento_Catalogo_Ericsson_5G_23.Q4_v2.xlsx",
    # },
]


# ---------------------------------------------------------------------------
# Funções de busca (modo automático)
# ---------------------------------------------------------------------------
def encontrar_xml(pasta_versao: Path, sufixo: str) -> Optional[Path]:
    """Procura, dentro da pasta da versão, um .xml terminado com o sufixo informado (case-insensitive)."""
    sufixo_lower = sufixo.lower()
    for arquivo in pasta_versao.glob("*.xml"):
        if arquivo.name.lower().endswith(sufixo_lower):
            return arquivo
    return None


def encontrar_pasta_vendor_mapeamento(vendor: str) -> Optional[Path]:
    """Encontra a pasta do vendor em MAPPING_ROOT (sem diferenciar maiúsculas/minúsculas)."""
    if not MAPPING_ROOT.exists():
        return None
    for pasta in MAPPING_ROOT.iterdir():
        if pasta.is_dir() and pasta.name.lower() == vendor.lower():
            return pasta
    return None


def encontrar_documentacao(vendor: str, versao: str) -> Optional[Path]:
    """
    Procura o .xlsx cujo nome contenha a versão. Se houver mais de um (_v1, _v2...),
    retorna o de maior número.
    """
    pasta_vendor = encontrar_pasta_vendor_mapeamento(vendor)
    if pasta_vendor is None:
        return None

    candidatos = [
        arq for arq in pasta_vendor.glob("*.xlsx")
        if versao.lower() in arq.stem.lower()
    ]
    if not candidatos:
        return None

    def numero_versao(caminho: Path) -> int:
        match = re.search(r"_v(\d+)$", caminho.stem, flags=re.IGNORECASE)
        return int(match.group(1)) if match else 0

    candidatos.sort(key=numero_versao, reverse=True)
    return candidatos[0]


# ---------------------------------------------------------------------------
# Execução comum (usada pelos dois modos)
# ---------------------------------------------------------------------------
def executar_catalogo(rotulo: str,
                      client_xml: Optional[Path],
                      oss_xml: Optional[Path],
                      operations_xml: Optional[Path],
                      documentacao: Optional[Path]) -> bool:
    """
    Valida os 4 arquivos e chama o articulador.
    Retorna True se processou, False se pulou.
    """
    print(f"\n>>> Processando: {rotulo}")
    print(f"    client       : {client_xml}")
    print(f"    oss          : {oss_xml}")
    print(f"    operations   : {operations_xml}")
    print(f"    documentacao : {documentacao}")

    arquivos = (
        ("client", client_xml),
        ("oss", oss_xml),
        ("operations", operations_xml),
        ("documentacao", documentacao),
    )

    # Faltando = não informado / não encontrado, ou caminho inexistente no disco
    faltando = [nome for nome, arq in arquivos if arq is None or not Path(arq).is_file()]
    if faltando:
        print(f"[ERRO] {rotulo}: arquivo(s) não encontrado(s): {', '.join(faltando)} -> pulando")
        return False

    articulador(client_xml, oss_xml, operations_xml, documentacao)
    return True


# ---------------------------------------------------------------------------
# Modo automático
# ---------------------------------------------------------------------------
def processar_catalogos() -> None:
    """Percorre todos os vendors/models(_CM_)/versões e processa cada conjunto encontrado."""
    if not CATALOGS_ROOT.exists():
        print(f"[ERRO] Diretório de catálogos não encontrado: {CATALOGS_ROOT}")
        return

    for vendor_dir in sorted(CATALOGS_ROOT.iterdir()):
        if not vendor_dir.is_dir():
            continue
        vendor = vendor_dir.name

        for model_dir in sorted(vendor_dir.iterdir()):
            if not model_dir.is_dir() or "_CM_" not in model_dir.name:
                continue

            for versao_dir in sorted(model_dir.iterdir()):
                if not versao_dir.is_dir():
                    continue
                versao = versao_dir.name

                executar_catalogo(
                    f"{vendor} / {model_dir.name} / {versao}",
                    encontrar_xml(versao_dir, XML_SUFFIXES["client"]),
                    encontrar_xml(versao_dir, XML_SUFFIXES["oss"]),
                    encontrar_xml(versao_dir, XML_SUFFIXES["operations"]),
                    encontrar_documentacao(vendor, versao),
                )


# ---------------------------------------------------------------------------
# Modo manual
# ---------------------------------------------------------------------------
def _to_path(valor) -> Optional[Path]:
    return Path(valor) if valor else None


def processar_manuais(catalogos: list) -> None:
    """Processa somente os catálogos informados manualmente."""
    if not catalogos:
        print("[AVISO] Nenhum catálogo manual informado (CATALOGOS_MANUAIS está vazio).")
        return

    for i, cat in enumerate(catalogos, start=1):
        executar_catalogo(
            f"manual #{i}",
            _to_path(cat.get("client")),
            _to_path(cat.get("oss")),
            _to_path(cat.get("operations")),
            _to_path(cat.get("documentacao")),
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(description="Altera catálogos CM (varredura completa ou manual).")
    p.add_argument("--client", help="Caminho do XML _client")
    p.add_argument("--oss", help="Caminho do XML _oss")
    p.add_argument("--operations", help="Caminho do XML _operations")
    p.add_argument("--documentacao", help="Caminho da planilha de mapeamento (.xlsx)")
    p.add_argument("--manual", action="store_true",
                   help="Processa apenas os catálogos listados em CATALOGOS_MANUAIS")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    manuais_cli = [args.client, args.oss, args.operations, args.documentacao]

    if any(manuais_cli):
        # Se passou algum argumento, exige os 4
        if not all(manuais_cli):
            print("[ERRO] No modo manual via CLI informe os 4: --client --oss --operations --documentacao")
            sys.exit(1)
        processar_manuais([{
            "client": args.client,
            "oss": args.oss,
            "operations": args.operations,
            "documentacao": args.documentacao,
        }])
    elif args.manual:
        processar_manuais(CATALOGOS_MANUAIS)
    else:
        processar_catalogos()