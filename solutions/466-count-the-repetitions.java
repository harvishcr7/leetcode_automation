import java.util.*;

class Solution {
    public int getMaxRepetitions(String s1, int n1, String s2, int n2) {
        if (n1 == 0) return 0;
        
        char[] c1 = s1.toCharArray();
        char[] c2 = s2.toCharArray();
        
        int len1 = c1.length;
        int len2 = c2.length;
        
        int[] repeatCount = new int[len2 + 1];
        int[] nextIndex = new int[len2 + 1];
        
        int j = 0;
        int count = 0;
        
        for (int k = 1; k <= n1; k++) {
            for (int i = 0; i < len1; i++) {
                if (c1[i] == c2[j]) {
                    j++;
                    if (j == len2) {
                        j = 0;
                        count++;
                    }
                }
            }
            
            repeatCount[k] = count;
            nextIndex[k] = j;
            
            for (int start = 0; start < k; start++) {
                if (nextIndex[start] == j) {
                    int prevRepeatCount = repeatCount[start];
                    int patternCount = ((n1 - start) / (k - start)) * (repeatCount[k] - prevRepeatCount);
                    int remainingCount = repeatCount[start + (n1 - start) % (k - start)] - prevRepeatCount;
                    return (prevRepeatCount + patternCount + remainingCount) / n2;
                }
            }
        }
        
        return repeatCount[n1] / n2;
    }
}