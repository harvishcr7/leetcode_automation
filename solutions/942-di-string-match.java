class Solution {
    public int[] diStringMatch(String s) {
        int n = s.length();
        int left = 0;
        int right = n;
        int[] perm = new int[n + 1];
        
        for (int i = 0; i < n; i++) {
            if (s.charAt(i) == 'I') {
                perm[i] = left++;
            } else {
                perm[i] = right--;
            }
        }
        perm[n] = left;
        
        return perm;
    }
}