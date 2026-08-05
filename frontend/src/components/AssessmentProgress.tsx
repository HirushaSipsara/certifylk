interface Props {
  currentStep: 1 | 2 | 3 | 4;
}

const labels = ["Product profile", "Manufacturing process", "Evidence", "Clarification"];

export function AssessmentProgress({ currentStep }: Props) {
  return (
    <div aria-label={`Assessment progress: step ${currentStep} of 4`}>
      <div className="mb-2 flex items-center justify-between text-sm font-semibold text-leaf">
        <span>Step {currentStep} of 4</span>
        <span>{labels[currentStep - 1]}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-emerald-100">
        <div
          className="h-full rounded-full bg-leaf transition-all"
          style={{ width: `${currentStep * 25}%` }}
        />
      </div>
    </div>
  );
}
