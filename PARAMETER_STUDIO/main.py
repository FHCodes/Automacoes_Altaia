#!/usr/bin/env python3
"""
Script para varrer o diretório de catálogos (catalogs_full), identificar os
models que contêm "_CM_" no nome, localizar os 3 XMLs (client, oss, operations)
de cada versão e encontrar a planilha de documentação correspondente em
C:\\PARAMETER_STUDIO\\Mapeamento_Catalogos.

Para cada conjunto encontrado, chama main(client, oss, operations, documentacao).

Estrutura esperada em catalogs_full:
    catalogs_full/<VENDOR>/<MODEL_com__CM__no_nome>/<VERSAO>/
        <MODEL>_client.xml
        <MODEL>_oss.xml
        <MODEL>_operations.xml

Estrutura esperada em Mapeamento_Catalogos:
    Mapeamento_Catalogos/<Vendor>/Mapeamento_Catalogo_<Vendor>_5G_<VERSAO>_v<N>.xlsx
"""

import re
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


def encontrar_xml(pasta_versao: Path, sufixo: str) -> Optional[Path]:
    """Procura, dentro da pasta da versão, um .xml terminado com o sufixo informado (case-insensitive)."""
    sufixo_lower = sufixo.lower()
    for arquivo in pasta_versao.glob("*.xml"):
        if arquivo.name.lower().endswith(sufixo_lower):
            return arquivo
    return None


def encontrar_pasta_vendor_mapeamento(vendor: str) -> Optional[Path]:
    """
    Encontra, dentro de MAPPING_ROOT, a pasta correspondente ao vendor,
    comparando os nomes sem diferenciar maiúsculas/minúsculas.
    Ex.: vendor "ERICSSON" -> pasta "Ericsson"
    """
    if not MAPPING_ROOT.exists():
        return None
    for pasta in MAPPING_ROOT.iterdir():
        if pasta.is_dir() and pasta.name.lower() == vendor.lower():
            return pasta
    return None


def encontrar_documentacao(vendor: str, versao: str) -> Optional[Path]:
    """
    Dentro da pasta de mapeamento do vendor, procura o .xlsx cujo nome contenha
    a versão informada. Se existir mais de um (ex.: _v1, _v2...), retorna o de
    maior número de versão.
    Padrão esperado: Mapeamento_Catalogo_<Vendor>_5G_<versao>_v<N>.xlsx
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
        # extrai o número após "_v" no final do nome (ex.: ..._v1 -> 1)
        match = re.search(r"_v(\d+)$", caminho.stem, flags=re.IGNORECASE)
        return int(match.group(1)) if match else 0

    candidatos.sort(key=numero_versao, reverse=True)
    return candidatos[0]


def processar_catalogos() -> None:
    """Percorre todos os vendors/models(_CM_)/versões e chama main() para cada conjunto encontrado."""
    if not CATALOGS_ROOT.exists():
        print(f"[ERRO] Diretório de catálogos não encontrado: {CATALOGS_ROOT}")
        return

    for vendor_dir in sorted(CATALOGS_ROOT.iterdir()):
        if not vendor_dir.is_dir():
            continue
        vendor = vendor_dir.name

        for model_dir in sorted(vendor_dir.iterdir()):
            if not model_dir.is_dir():
                continue
            if "_CM_" not in model_dir.name:
                continue  # só nos interessam os catálogos de CM

            for versao_dir in sorted(model_dir.iterdir()):
                if not versao_dir.is_dir():
                    continue
                versao = versao_dir.name

                client_xml = encontrar_xml(versao_dir, XML_SUFFIXES["client"])
                oss_xml = encontrar_xml(versao_dir, XML_SUFFIXES["oss"])
                operations_xml = encontrar_xml(versao_dir, XML_SUFFIXES["operations"])
                documentacao = encontrar_documentacao(vendor, versao)

                print(f"\n>>> Processando: {vendor} / {model_dir.name} / {versao}")
                print(f"    client       : {client_xml}")
                print(f"    oss          : {oss_xml}")
                print(f"    operations   : {operations_xml}")
                print(f"    documentacao : {documentacao}")

                # Verifica se algum dos 4 arquivos não foi encontrado. Se faltar
                # algo, avisa e segue para o próximo catálogo (não interrompe o loop).
                faltando = [
                    nome for nome, arq in (
                        ("client", client_xml),
                        ("oss", oss_xml),
                        ("operations", operations_xml),
                        ("documentacao", documentacao),
                    ) if arq is None
                ]
                if faltando:
                    print(f"[ERRO] {vendor}/{model_dir.name}/{versao}: "
                          f"arquivo(s) não encontrado(s): {', '.join(faltando)} -> pulando para o próximo catálogo")
                    continue

                articulador(client_xml, oss_xml, operations_xml, documentacao)
               


def main(client: Optional[Path], oss: Optional[Path], operations: Optional[Path],
         documentacao: Optional[Path]) -> None:
    """
    Função principal, executada para cada conjunto (client, oss, operations, documentacao)
    encontrado durante a varredura.

    >>> AJUSTE AQUI a lógica de negócio que você quer aplicar a cada catálogo <<<
    """
    # TODO: implementar a lógica de negócio (ex.: comparar XML com o xlsx, gerar relatório, etc.)
    pass


if __name__ == "__main__":
    processar_catalogos()