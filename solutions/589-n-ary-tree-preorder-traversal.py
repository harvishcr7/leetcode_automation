class Solution:
    def preorder(self, root: 'Node') -> List[int]:
        if not root:
            return []
        
        stack = [root]
        output = []
        
        while stack:
            node = stack.pop()
            output.append(node.val)
            if node.children:
                for child in reversed(node.children):
                    if child:
                        stack.append(child)
                        
        return output