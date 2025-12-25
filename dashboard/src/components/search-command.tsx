import { useSearch } from "@/api/endpoints/search/search";
import { pushModal } from "@/components/push-modals";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { Kbd } from "@/components/ui/kbd";
import { Spinner } from "@/components/ui/spinner";
import { useDebounce } from "@/hooks/use-debounce";
import { useNavigate } from "@tanstack/react-router";
import {
  ArrowUpRightIcon,
  BoxIcon,
  PackagePlusIcon,
  PlusIcon,
  ReceiptTextIcon,
  SearchIcon,
  UserIcon,
  UserPlusIcon,
} from "lucide-react";
import * as React from "react";

type Item =
  | {
      key: string;
      label: string;
      href: string;
      icon?: React.ComponentType<any>;
      leading?: never;
    }
  | {
      key: string;
      label: string;
      onClick: () => void;
      icon?: React.ComponentType<any>;
      leading?: never;
    }
  | {
      key: string;
      label: string;
      href: string;
      leading: React.ReactNode;
      icon?: never;
    };

type Section = { heading: string; items: Item[] };

export function SearchCommand() {
  const navigate = useNavigate();
  const [open, setOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");
  const debounced = useDebounce(search, 400);

  const { data, isFetching } = useSearch(
    { search: debounced },
    { query: { enabled: debounced.length > 0 } },
  );

  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  const isWorking =
    search.trim().length > 0 && (search !== debounced || isFetching);
  const qn = search.trim().toLowerCase();

  const staticSections: Section[] = [
    {
      heading: "Actions",
      items: [
        // TODO: add new invoice action somehow
        {
          key: "new-customer",
          label: "Create new customer",
          icon: UserPlusIcon,
          onClick: () => pushModal("CustomerCreateSheet", { name: "" }),
        },
        {
          key: "new-product",
          label: "Create new product",
          icon: PackagePlusIcon,
          onClick: () => pushModal("ProductCreateSheet", { name: "" }),
        },
        {
          key: "new-coupon",
          label: "Create new coupon",
          icon: PlusIcon,
          onClick: () => pushModal("CouponCreateSheet", { name: "" }),
        },
        {
          key: "new-tax-rate",
          label: "Create new tax rate",
          icon: PlusIcon,
          onClick: () => pushModal("TaxRateCreateSheet", { name: "" }),
        },
      ],
    },
    {
      heading: "Navigation",
      items: [
        {
          key: "nav-overview",
          label: "Go to overview",
          icon: ArrowUpRightIcon,
          href: "/overview",
        },
        {
          key: "nav-invoices",
          label: "Go to invoices",
          icon: ArrowUpRightIcon,
          href: "/invoices",
        },
        {
          key: "nav-quotes",
          label: "Go to quotes",
          icon: ArrowUpRightIcon,
          href: "/quotes",
        },
        {
          key: "nav-customers",
          label: "Go to customers",
          icon: ArrowUpRightIcon,
          href: "/customers",
        },
        {
          key: "nav-products",
          label: "Go to products",
          icon: ArrowUpRightIcon,
          href: "/products",
        },
        {
          key: "nav-coupons",
          label: "Go to coupons",
          icon: ArrowUpRightIcon,
          href: "/coupons",
        },
        {
          key: "nav-tax-rates",
          label: "Go to tax rates",
          icon: ArrowUpRightIcon,
          href: "/tax-rates",
        },
        {
          key: "nav-set-account",
          label: "Go to account settings",
          icon: ArrowUpRightIcon,
          href: "/settings/account",
        },
        {
          key: "nav-set-billing",
          label: "Go to billing settings",
          icon: ArrowUpRightIcon,
          href: "/settings/billing",
        },
        {
          key: "nav-set-profile",
          label: "Go to profile settings",
          icon: ArrowUpRightIcon,
          href: "/settings/profile",
        },
      ],
    },
  ];

  const filteredStatic: Section[] =
    qn === ""
      ? staticSections
      : staticSections
          .map((s) => ({
            ...s,
            items: s.items.filter((it) => it.label.toLowerCase().includes(qn)),
          }))
          .filter((s) => s.items.length > 0);

  const dynamicSections: Section[] = isWorking
    ? []
    : ([
        data?.invoices?.length
          ? {
              heading: "Invoices",
              items: data.invoices.map((inv: any) => ({
                key: inv.id,
                label: inv.number ?? inv.id,
                href: `/invoices/${inv.id}`,
                icon: ReceiptTextIcon,
              })),
            }
          : null,
        data?.customers?.length
          ? {
              heading: "Customers",
              items: data.customers.map((c: any) => ({
                key: c.id,
                label: c.name,
                href: `/customers/${c.id}`,
                leading: (
                  <Avatar className="size-4 rounded-md">
                    <AvatarImage src={c.logo_url || undefined} alt={c.name} />
                    <AvatarFallback className="rounded-md">
                      <UserIcon />
                    </AvatarFallback>
                  </Avatar>
                ),
              })),
            }
          : null,
        data?.products?.length
          ? {
              heading: "Products",
              items: data.products.map((p: any) => ({
                key: p.id,
                label: p.name,
                href: `/products/${p.id}`,
                leading: (
                  <Avatar className="size-4 rounded-md">
                    <AvatarImage src={p.image_url || undefined} alt={p.name} />
                    <AvatarFallback className="rounded-md">
                      <BoxIcon />
                    </AvatarFallback>
                  </Avatar>
                ),
              })),
            }
          : null,
      ].filter(Boolean) as Section[]);

  const sectionsToRender = [...filteredStatic, ...dynamicSections];

  const handleSelect = async (item: Item) => {
    if ("href" in item) await navigate({ to: item.href });
    if ("onClick" in item) item.onClick();
    setOpen(false);
  };

  return (
    <>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="text-muted-foreground gap-0"
        onClick={() => setOpen(true)}
      >
        <SearchIcon className="mr-2" />
        <span>Search</span>
        <Kbd>K</Kbd>
      </Button>

      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput
          placeholder="Type a command or search…"
          value={search}
          onValueChange={setSearch}
          autoFocus
        />
        <CommandList>
          <CommandEmpty>
            {isWorking ? (
              <Spinner variant="background" />
            ) : sectionsToRender.length === 0 ? (
              "No results found"
            ) : null}
          </CommandEmpty>

          {sectionsToRender.map((section, i) => (
            <React.Fragment key={section.heading}>
              <CommandGroup heading={section.heading}>
                {section.items.map((item) => (
                  <CommandItem
                    key={item.key}
                    value={`${item.label}::${item.key}`}
                    onSelect={() => handleSelect(item)}
                  >
                    {"leading" in item ? (
                      item.leading
                    ) : "icon" in item && item.icon ? (
                      <item.icon />
                    ) : null}
                    <span>{item.label}</span>
                  </CommandItem>
                ))}
              </CommandGroup>
              {i < sectionsToRender.length - 1 && <CommandSeparator />}
            </React.Fragment>
          ))}
        </CommandList>
      </CommandDialog>
    </>
  );
}
