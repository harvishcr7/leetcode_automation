class Solution:
    def findRestaurant(self, list1: list[str], list2: list[str]) -> list[str]:
        map1 = {val: i for i, val in enumerate(list1)}
        min_sum = float('inf')
        result = []
        
        for j, val in enumerate(list2):
            if val in map1:
                index_sum = j + map1[val]
                if index_sum < min_sum:
                    min_sum = index_sum
                    result = [val]
                elif index_sum == min_sum:
                    result.append(val)
                    
        return result