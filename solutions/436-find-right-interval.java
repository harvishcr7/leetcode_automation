import java.util.Arrays;
import java.util.TreeMap;

class Solution {
    public int[] findRightInterval(int[][] intervals) {
        int n = intervals.length;
        int[] result = new int[n];
        TreeMap<Integer, Integer> startMap = new TreeMap<>();
        
        for (int i = 0; i < n; i++) {
            startMap.put(intervals[i][0], i);
        }
        
        for (int i = 0; i < n; i++) {
            int end = intervals[i][1];
            Integer key = startMap.ceilingKey(end);
            if (key != null) {
                result[i] = startMap.get(key);
            } else {
                result[i] = -1;
            }
        }
        
        return result;
    }
}