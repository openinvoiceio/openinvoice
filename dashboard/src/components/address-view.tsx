import type { Address } from "@/api/models";
import { formatCountry } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import React from "react";

export function AddressView({
  address,
  className,
  ...props
}: React.ComponentProps<"div"> & {
  address?: Address;
}) {
  const hasAddress = Boolean(
    address?.line1 ||
    address?.line2 ||
    address?.postal_code ||
    address?.locality ||
    address?.state ||
    address?.country,
  );

  if (!hasAddress) return <span>-</span>;

  return (
    <div className={cn("flex flex-col", className)} {...props}>
      {address?.line1 && <div>{address.line1}</div>}
      {address?.line2 && <div>{address.line2}</div>}
      <div>
        {address?.postal_code && (
          <span>
            {address.postal_code}
            {address.locality && ", "}
          </span>
        )}
        {address?.locality && <span>{address.locality}</span>}
      </div>
      <div>
        {address?.state && (
          <span>
            {address.state}
            {address.country && ", "}
          </span>
        )}
        {address?.country && <span>{formatCountry(address.country)}</span>}
      </div>
    </div>
  );
}
