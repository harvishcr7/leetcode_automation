class Solution:
    def maxProduct(self, words: list[str]) -> int:
        masks = {}
        for w in words:
            mask = 0
            for ch in w:
                mask |= 1 << (ord(ch) - 97)
            masks[mask] = max(masks.get(mask, 0), len(w))

        max_prod = 0
        mask_items = list(masks.items())
        n = len(mask_items)
        for i in range(n):
            m1, l1 = mask_items[i]
            for j in range(i + 1, n):
                m2, l2 = mask_items[j]
                if m1 & m2 == 0:
                    prod = l1 * l2
                    if prod > max_prod:
                        max_prod = prod

        return max_prod