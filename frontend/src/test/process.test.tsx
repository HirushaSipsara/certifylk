import { render, screen } from "@testing-library/react";
import { useForm } from "react-hook-form";

import { ProcessStepList, type ProcessFormValues } from "@/components/ProcessStepList";

function Harness() {
  const { register } = useForm<ProcessFormValues>({
    defaultValues: { steps: ["", "", "", "", ""] },
  });
  return <ProcessStepList register={register} />;
}

test("process input renders exactly five ordered step controls", () => {
  render(<Harness />);
  expect(screen.getAllByRole("textbox")).toHaveLength(5);
  expect(screen.getByLabelText("Production step 1")).toBeInTheDocument();
  expect(screen.getByLabelText("Production step 5")).toBeInTheDocument();
});
