const DEFAULT_TITLE = "流程中心";

export function setPageTitle(title: string | null | undefined) {
  const nextTitle = title?.trim() || DEFAULT_TITLE;
  document.title = nextTitle;
}
