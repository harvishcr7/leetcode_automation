class SummaryRanges:

    def __init__(self):
        self.intervals = []

    def addNum(self, value: int) -> None:
        from bisect import bisect_right
        
        idx = bisect_right(self.intervals, value, key=lambda x: x[0])
        i = idx - 1

        if i >= 0 and self.intervals[i][0] <= value <= self.intervals[i][1]:
            return

        if i >= 0 and self.intervals[i][1] + 1 == value:
            if idx < len(self.intervals) and self.intervals[idx][0] == value + 1:
                self.intervals[i][1] = self.intervals[idx][1]
                del self.intervals[idx]
            else:
                self.intervals[i][1] = value
        elif idx < len(self.intervals) and self.intervals[idx][0] == value + 1:
            self.intervals[idx][0] = value
        else:
            self.intervals.insert(idx, [value, value])

    def getIntervals(self) -> list[list[int]]:
        return self.intervals