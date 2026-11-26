import java.util.Arrays;

class Solution {
    public int smallestRangeI(int[] nums, int k) {
        int min = nums[0];
        int max = nums[0];
        for (int i = 1; i < nums.length; i++) {
            if (nums[i] < min) {
                min = nums[i];
            }
            if (nums[i] > max) {
                max = nums[i];
            }
        }
        int diff = (max - k) - (min + k);
        return diff < 0 ? 0 : diff;
    }
}