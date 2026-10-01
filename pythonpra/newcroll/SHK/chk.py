import FinanceDataReader as fdr
print(fdr.DataReader("KS11", "2026-09-10").tail(8))
print(fdr.DataReader("005930", "2026-09-10").tail(3))