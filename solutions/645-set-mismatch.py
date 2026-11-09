class Solution:
    def findErrorNums(self, nums: list[int]) -> list[int]:
        n = len(nums)
        actual_sum = sum(nums)
        actual_sum_sq = sum(x * x for x in nums)
        
        expected_sum = n * (n + 1) // 2
        expected_sum_sq = n * (n + 1) * (2 * n + 1) // 6
        
        diff = actual_sum - expected_sum
        diff_sq = actual_sum_sq - expected_sum_sq
        
        sum_xy = diff_sq // diff
        
        duplicate = (diff + sum_xy) // 2
        missing = sum_xy - duplicate
        
        return [duplicate, missing]