import os, re
from openpyxl import load_workbook
from string import Template

#=#=#= CONFIGURAÇÕES =#=##=

tipo = "pm"  # Apenas muda o nome da pasta
vendor = "ericsson_pm"  #Nome da aba do excell(Pode dar erro se não mudar)

#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=


XLSX = f"SYNCs.xlsx"
SHEET = vendor.upper()


OUT_CRON = f"{tipo}_cronjobs"
OUT_CUSTOM = f"{tipo}_customization"

SCHEDULE = "0 7 * * 1-5"  # se vier "A ver"


def s(v): return "" if v is None else str(v).strip()

def read_rows(xlsx, sheet=None):
    wb = load_workbook(xlsx, data_only=True)
    ws = wb[sheet] if sheet else wb.active
    headers = [re.sub(r"\s+", " ", s(c.value)) for c in ws[1]]
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        d = {headers[i]: r[i] for i in range(len(headers))}
        if all(s(v) == "" for v in d.values()):
            continue
        rows.append(d)
    return rows

def parse_mascara_to_list(txt):
    # pega itens ""ITEM""
    items = re.findall(r'""(.*?)""', s(txt), flags=re.DOTALL)
    if not items:  # fallback "ITEM"
        items = re.findall(r'"(.*?)"', s(txt), flags=re.DOTALL)
    return [i.strip() for i in items if i.strip()]

def yaml_inline_list(items):
    # gera: ["a", "b", "c"] com aspas duplas e escapando o que precisar
    def esc(x: str) -> str:
        x = x.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{x}"'
    return "[" + ", ".join(esc(i) for i in items) + "]"


from string import Template
import os

def main():
    os.makedirs(OUT_CRON, exist_ok=True)
    os.makedirs(OUT_CUSTOM, exist_ok=True)

    errors = []

    for i, row in enumerate(read_rows(XLSX, SHEET), start=1):
        cronjob_name = None
        yml_name = None
        ip = None

        try:
            # --- nomes de templates vindos do Excel (AGORA EM MAIÚSCULO) ---
            tipo = s(row["TIPO"])  # KeyError se não existir
            TEMPLATE_CRON = f"{tipo}.yaml"
            TEMPLATE_CUSTOM = f"{tipo}.yml"

            # --- ler templates ---
            try:
                with open(TEMPLATE_CRON, "r", encoding="utf-8") as f:
                    cron_tpl = Template(f.read())
            except FileNotFoundError as e:
                raise FileNotFoundError(f"Template Cron não encontrado: {TEMPLATE_CRON}") from e

            try:
                with open(TEMPLATE_CUSTOM, "r", encoding="utf-8") as f:
                    cust_tpl = Template(f.read())
            except FileNotFoundError as e:
                raise FileNotFoundError(f"Template Custom não encontrado: {TEMPLATE_CUSTOM}") from e

            # --- campos principais (AGORA EM MAIÚSCULO) ---
            cronjob_name = s(row["CRONJOB_NAME"])
            ip = s(row["IP_COLETA"])
            yml_name = s(row["YML_NAME"])

            custom_file = f"{yml_name}_{ip}.yml"

            # --- variáveis para substituir ---
            vars_ = {k: s(v) for k, v in row.items()}

            # Se você quer forçar o schedule do código, sobrescreve
            vars_["SCHEDULE"] = SCHEDULE

            # Se você quer usar o schedule que vem do Excel, comente a linha acima
            # e garanta que a coluna SCHEDULE esteja preenchida.

            vars_["CUSTOM_FILE"] = custom_file

            # Mascara vira lista YAML (coluna agora é MASCARA)
            mask_list = parse_mascara_to_list(row.get("MASCARA"))
            vars_["MASCARA_LIST"] = yaml_inline_list(mask_list)

            # PERIOD agora é PERIOD (sem espaço no header)
            vars_["PERIOD"] = s(row.get("PERIOD"))

            # Login/senha (agora LOGIN/PASSWORD)
            vars_["LOGIN"] = s(row.get("LOGIN"))
            vars_["PASSWORD"] = s(row.get("PASSWORD"))

            # --- render ---
            cron_out = cron_tpl.safe_substitute(vars_)
            cust_out = cust_tpl.safe_substitute(vars_)

            # --- escrever outputs ---
            with open(f"{OUT_CRON}/{cronjob_name}.yaml", "w", encoding="utf-8") as f:
                f.write(cron_out)

            with open(f"{OUT_CUSTOM}/{custom_file}", "w", encoding="utf-8") as f:
                f.write(cust_out)

        except KeyError as e:
            msg = f"[linha {i}] Coluna ausente no Excel: {e}. cronjob={cronjob_name} tipo={row.get('TIPO')}"
            print("ERRO:", msg)
            errors.append(msg)
            continue

        except Exception as e:
            msg = f"[linha {i}] Falha ao gerar. cronjob={cronjob_name} yml={yml_name} ip={ip} erro={type(e).__name__}: {e}"
            print("ERRO:", msg)
            errors.append(msg)
            continue

    if errors:
        print(f"\nConcluído com {len(errors)} erro(s). Veja acima os detalhes.")
    else:
        print("OK! Gerado em:", OUT_CRON, "e", OUT_CUSTOM)


if __name__ == "__main__":
    main()
