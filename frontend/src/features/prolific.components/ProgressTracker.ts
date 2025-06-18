export interface ProgressPoint {
  label: string;
  completed: boolean;
}

export default class ProgressTracker {
  public progressPoints: ProgressPoint[];
  public currentIndex: number;

  constructor(labels: string[] = []) {
    this.progressPoints = labels.map(label => ({
      label,
      completed: false,
    }));
    this.currentIndex = 0;
  }

  get current(): ProgressPoint | undefined {
    if (this.progressPoints.length === 0) {
      return undefined;
    }
    return this.progressPoints[this.currentIndex];
  }

  public advance(): void {
    if (this.currentIndex < this.progressPoints.length) {
      this.progressPoints[this.currentIndex].completed = true;
      if (this.currentIndex < this.progressPoints.length - 1) {
        this.currentIndex++;
      }
    }
  }

  public goBack(): void {
    if (this.currentIndex > 0) {
      // As per plan, goBack does not reset completion status of the point it's moving from.
      // It only moves the currentIndex. If reset is desired, logic needs to be added here.
      this.currentIndex--;
    }
  }

  public isLineActive(lineIndex: number): boolean {
    // lineIndex refers to the index of the *first* point of the two points the line connects.
    // So, the line between progressPoints[lineIndex] and progressPoints[lineIndex + 1].
    // This line is active if progressPoints[lineIndex] is completed.
    if (lineIndex >= 0 && lineIndex < this.progressPoints.length) {
      return this.progressPoints[lineIndex].completed;
    }
    return false;
  }
}
