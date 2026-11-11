import java.util.*;

class Solution {
    public int lengthLongestPath(String input) {
        Stack<Integer> stack = new Stack<>();
        stack.push(0); 
        int maxLength = 0;
        
        String[] lines = input.split("\n");
        
        for (String line : lines) {
            int level = line.lastIndexOf("\t") + 1;
            
            while (level + 1 < stack.size()) {
                stack.pop();
            }
            
            int len = stack.peek() + line.length() - level + 1;
            stack.push(len);
            
            if (line.contains(".")) {
                maxLength = Math.max(maxLength, len - 1);
            }
        }
        
        return maxLength;
    }
}