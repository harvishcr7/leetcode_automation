class Solution:
    def maxCount(self, m: int, n: int, ops: list[list[int]]) -> int:
        if not ops:
            return m * n
        min_a = m
        min_b = n
        for a, b in ops:
            if a < min_a:
                min_a = a
            if b < min_b:
                min_b = b
        return min_a * min_b