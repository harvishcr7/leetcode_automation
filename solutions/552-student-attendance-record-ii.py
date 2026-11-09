class Solution:
    def checkRecord(self, n: int) -> int:
        MOD = 10**9 + 7
        
        a0l0 = 1
        a0l1 = 0
        a0l2 = 0
        a1l0 = 0
        a1l1 = 0
        a1l2 = 0

        for _ in range(n):
            next_a0l0 = (a0l0 + a0l1 + a0l2) % MOD
            next_a0l1 = a0l0
            next_a0l2 = a0l1

            next_a1l0 = (a1l0 + a1l1 + a1l2 + a0l0 + a0l1 + a0l2) % MOD
            next_a1l1 = a1l0
            next_a1l2 = a1l1

            a0l0, a0l1, a0l2 = next_a0l0, next_a0l1, next_a0l2
            a1l0, a1l1, a1l2 = next_a1l0, next_a1l1, next_a1l2

        return (a0l0 + a0l1 + a0l2 + a1l0 + a1l1 + a1l2) % MOD