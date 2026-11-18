"""Executa os cenários de avaliação.

    python -m evals.run                 # imprime o resultado
    python -m evals.run --salvar        # também grava evals/relatorio.md
Sai com código 1 se alguma verificação falhar.
"""
import argparse
import sys
from pathlib import Path

from evals.cenarios import CENARIOS

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--salvar", action="store_true", help="grava evals/relatorio.md")
    args = parser.parse_args()

    linhas = ["# Relatório de evals", "", "| Cenário | Verificações | Resultado |", "|---|---|---|"]
    detalhes, total, ok_total = [], 0, 0
    for nome, cenario in CENARIOS.items():
        try:
            verificacoes = cenario()
        except Exception as exc:  # um cenário quebrado conta como falha, não derruba o resto
            from evals.cenarios import Verificacao
            verificacoes = [Verificacao("execução do cenário", False, repr(exc))]
        ok = sum(1 for x in verificacoes if x.ok)
        total += len(verificacoes)
        ok_total += ok
        status = "PASSOU" if ok == len(verificacoes) else "FALHOU"
        linhas.append(f"| {nome} | {ok}/{len(verificacoes)} | {status} |")
        print(f"[{status}] {nome} ({ok}/{len(verificacoes)})")
        for x in verificacoes:
            if not x.ok:
                print(f"    x {x.nome}: {x.detalhe}")
                detalhes.append(f"- **{nome}**: {x.nome} — {x.detalhe}")

    print(f"\nTotal: {ok_total}/{total} verificações")
    if args.salvar:
        linhas += ["", f"**Total: {ok_total}/{total} verificações.**"]
        if detalhes:
            linhas += ["", "## Falhas", *detalhes]
        Path(__file__).with_name("relatorio.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return 0 if ok_total == total else 1

if __name__ == "__main__":
    sys.exit(main())
