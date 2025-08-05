export function LangGraphLogoSVG({
  className,
  width = 80,
  height = 80,
}: {
  width?: number;
  height?: number;
  className?: string;
}) {
  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Bold chat bubble */}
      <rect x="5" y="5" width="90" height="90" rx="20" fill="#2196F3" />

      {/* Bold medical cross */}
      <path
        d="M65 45H55V35H45V45H35V55H45V65H55V55H65V45Z"
        fill="white"
      />
    </svg>
  );
}
