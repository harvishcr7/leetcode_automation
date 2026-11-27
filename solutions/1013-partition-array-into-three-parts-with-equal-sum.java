class Solution {
    public boolean canThreePartsEqualSum(int[] arr) {
        int totalSum = 0;
        for (int num : arr) {
            totalSum += num;
        }
        
        if (totalSum % 3 != 0) {
            return false;
        }
        
        int target = totalSum / 3;
        int currentSum = 0;
        int count = 0;
        
        for (int i = 0; i < arr.length; i++) {
            currentSum += arr[i];
            if (currentSum == target) {
                count++;
                currentSum = 0;
                if (count == 2) {
                    return i < arr.length - 1;
                }
            }
        }
        
        return false;
    }
}