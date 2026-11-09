# Definition for a binary tree node.
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right
class Solution:
    def binaryTreePaths(self, root: TreeNode | None) -> list[str]:
        if not root:
            return []
        
        paths = []
        
        def dfs(node, current_path):
            if not node.left and not node.right:
                paths.append(current_path + str(node.val))
                return
            if node.left:
                dfs(node.left, current_path + str(node.val) + "->")
            if node.right:
                dfs(node.right, current_path + str(node.val) + "->")
                
        dfs(root, "")
        return paths