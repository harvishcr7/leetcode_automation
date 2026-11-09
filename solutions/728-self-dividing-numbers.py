class Solution:
    def selfDividingNumbers(self, left: int, right: int) -> list[int]:
        def is_self_dividing(n: int) -> bool:
            temp = n
            while temp > 0:
                digit = temp % 10
                if digit == 0 or n % digit != 0:
                    return False
                temp //= 10
            return True

        return [num for num in range(left, right + 1) if is_self_dividing(num)]