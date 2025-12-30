import { Suspense } from "react";
import DrivePageSection from "@/components/drive/drive-page-section";
import DrivePageSkeleton from "@/components/drive/drive-page-skeleton";
export const dynamic = "force-dynamic";

export default async function DrivePage() {
  return (
    <Suspense fallback={<DrivePageSkeleton />}>
      <DrivePageSection />
    </Suspense>
  );
}
