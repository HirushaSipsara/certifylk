interface Props {
  message: string;
  onRetry?: () => void;
}

export function ErrorAlert({ message, onRetry }: Props) {
  return (
    <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-800">
      <p>{message}</p>
      {onRetry ? (
        <button type="button" onClick={onRetry} className="mt-2 font-bold underline">
          Retry
        </button>
      ) : null}
    </div>
  );
}
