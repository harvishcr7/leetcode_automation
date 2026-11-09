# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def findMode(self, root: TreeNode | None) -> list[int]:
        self.max_streak = 0
        self.curr_streak = 0
        self.curr_val = None
        self.modes = []

        def inorder(node):
            if not node:
                return
            
            inorder(node.left)
            
            if node.val == self.curr_val:
                self.curr_streak += 1
            else:
                self.curr_streak = 1
                self.curr_val = node.val
                
            if self.curr_streak > self.max_streak:
                self.max_streak = self.curr_streak
                self.modes = [self.curr_val]
            elif self.curr_streak == self.max_streak:
                self.modes.append(self.curr_val)
                
            inorder(node.right)

        inorder(root)
        return self.modes