class Solution:
    def shortestCompletingWord(self, licensePlate: str, words: list[str]) -> str:
        from collections import Counter
        
        plate_counts = Counter(c.lower() for c in licensePlate if c.isalpha())
        
        shortest_word = None
        
        for word in words:
            word_counts = Counter(word)
            is_completing = True
            for char, count in plate_counts.items():
                if word_counts[char] < count:
                    is_completing = False
                    break
            
            if is_completing:
                if shortest_word is None or len(word) < len(shortest_word):
                    shortest_word = word
                    
        return shortest_word