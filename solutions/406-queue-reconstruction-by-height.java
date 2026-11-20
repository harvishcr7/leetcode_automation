import java.util.Arrays;
import java.util.ArrayList;
import java.util.List;

class Solution {
    public int[][] reconstructQueue(int[][] people) {
        Arrays.sort(people, (a, b) -> {
            if (a[0] != b[0]) {
                return Integer.compare(b[0], a[0]);
            } else {
                return Integer.compare(a[1], b[1]);
            }
        });

        List<int[]> reconstructed = new ArrayList<>();
        for (int[] person : people) {
            reconstructed.add(person[1], person);
        }

        return reconstructed.toArray(new int[people.length][]);
    }
}