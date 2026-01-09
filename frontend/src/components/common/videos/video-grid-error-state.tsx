import { Alert, AlertDescription } from "@/components/ui/alert";

type VideoGridErrorStateProps = {
  message: string;
};

export default function VideoGridErrorState({
  message,
}: VideoGridErrorStateProps) {
  return (
    <Alert className="bg-red-500/10 border-red-500/20">
      <AlertDescription className="text-red-400">
        {message}
      </AlertDescription>
    </Alert>
  );
}
