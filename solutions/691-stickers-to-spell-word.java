import java.util.*;

class Solution {
    public int minStickers(String[] stickers, String target) {
        int n = stickers.length;
        int[][] stickerCounts = new int[n][26];
        for (int i = 0; i < n; i++) {
            for (char c : stickers[i].toCharArray()) {
                stickerCounts[i][c - 'a']++;
            }
        }

        int m = target.length();
        int targetStates = 1 << m;
        int[] dp = new int[targetStates];
        Arrays.fill(dp, -1);
        dp[0] = 0;

        char[] targetChars = target.toCharArray();

        for (int mask = 0; mask < targetStates; mask++) {
            if (dp[mask] == -1) continue;

            for (int i = 0; i < n; i++) {
                int nextMask = mask;
                int[] count = stickerCounts[i].clone();

                for (int j = 0; j < m; j++) {
                    if ((nextMask & (1 << j)) == 0) {
                        int c = targetChars[j] - 'a';
                        if (count[c] > 0) {
                            count[c]--;
                            nextMask |= (1 << j);
                        }
                    }
                }

                if (dp[nextMask] == -1 || dp[nextMask] > dp[mask] + 1) {
                    dp[nextMask] = dp[mask] + 1;
                }
            }
        }

        return dp[targetStates - 1];
    }
}