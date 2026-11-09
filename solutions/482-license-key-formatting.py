class Solution:
    def licenseKeyFormatting(self, s: str, k: int) -> str:
        s = s.replace("-", "").upper()
        n = len(s)
        
        first_group_len = n % k if n % k != 0 else k
        
        res = [s[:first_group_len]]
        for i in range(first_group_len, n, k):
            res.append(s[i:i+k])
            
        return "-".join(res)