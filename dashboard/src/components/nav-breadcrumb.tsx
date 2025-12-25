import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Link, useLocation, useNavigate } from "@tanstack/react-router";
import { type LucideIcon } from "lucide-react";
import { Fragment } from "react";

interface NavBreadcrumbProps {
  items: (
    | {
        type: "link";
        label: string;
        href: string;
      }
    | {
        type: "page";
        label: string;
      }
    | {
        type: "select";
        items: {
          value: string;
          label: string;
          icon: LucideIcon;
          enabled?: boolean;
        }[];
      }
  )[];
}

export function NavBreadcrumb({ items }: NavBreadcrumbProps) {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Breadcrumb>
      <BreadcrumbList>
        {items.map((item, i) => (
          <Fragment key={i}>
            <BreadcrumbItem>
              {item.type === "link" ? (
                <BreadcrumbLink className="hidden md:block" asChild>
                  <Link to={item.href}>{item.label}</Link>
                </BreadcrumbLink>
              ) : null}
              {item.type === "page" ? (
                <BreadcrumbPage className="hidden max-w-[120px] truncate md:block lg:max-w-[200px]">
                  {item.label}
                </BreadcrumbPage>
              ) : null}
              {item.type === "select" ? (
                <Select
                  value={location.pathname}
                  onValueChange={(value) => navigate({ to: value })}
                >
                  <SelectTrigger className="text-foreground [&>span_svg]:text-muted-foreground/80 [&>span]:flex [&>span]:items-center [&>span]:gap-2 [&>span_svg]:shrink-0">
                    <SelectValue placeholder="Select option" />
                  </SelectTrigger>
                  <SelectContent>
                    {item.items
                      .filter((item) => item.enabled !== false)
                      .map((item, i) => (
                        <SelectItem key={i} value={item.value}>
                          <item.icon size={16} aria-hidden="true" />
                          {item.label}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              ) : null}
            </BreadcrumbItem>
            {i < items.length - 1 && (
              <BreadcrumbSeparator className="hidden md:block" />
            )}
          </Fragment>
        ))}
      </BreadcrumbList>
    </Breadcrumb>
  );
}
