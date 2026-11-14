import java.util.*;

class Solution {
    public int removeBoxes(int[] boxes) {
        int n = boxes.length;
        int[][][] dp = new int[n][n][n];
        return calculatePoints(boxes, 0, n - 1, 0, dp);
    }

    private int calculatePoints(int[] boxes, int l, int r, int k, int[][][] dp) {
        if (l > r) {
            return 0;
        }
        if (dp[l][r][k] != 0) {
            return dp[l][r][k];
        }

        int originalL = l;
        int originalK = k;

        while (l + 1 <= r && boxes[l + 1] == boxes[l]) {
            l++;
            k++;
        }

        int res = (k + 1) * (k + 1) + calculatePoints(boxes, l + 1, r, 0, dp);

        for (int m = l + 1; m <= r; m++) {
            if (boxes[m] == boxes[l]) {
                res = Math.max(res, calculatePoints(boxes, l + 1, m - 1, 0, dp) + calculatePoints(boxes, m, r, k + 1, dp));
            }
        }

        dp[originalL][r][originalK] = res;
        return res;
    }
}