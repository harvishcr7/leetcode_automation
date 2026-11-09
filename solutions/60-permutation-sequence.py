class Solution:
    def getPermutation(self, n: int, k: int) -> str:
        numbers = [str(i) for i in range(1, n + 1)]
        k -= 1
        
        import math
        fact = math.factorial(n - 1)
        res = []
        
        for i in range(n - 1, 0, -1):
            idx = k // fact
            res.append(numbers.pop(idx))
            k %= fact
            fact //= i
            
        res.append(numbers[0])
        return "".join(res)