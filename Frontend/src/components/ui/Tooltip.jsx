import { cloneElement } from 'react';

/** CSS-only tooltip (no JS positioning library): wraps a single focusable
 * child, shows `label` above it on hover/focus via group-hover/group-focus. */
function Tooltip({ label, children }) {
  return (
    <span className="group relative inline-flex">
      {cloneElement(children, { 'aria-describedby': undefined })}
      <span
        role="tooltip"
        className="pointer-events-none absolute bottom-full left-1/2 z-20 mb-1.5 -translate-x-1/2 whitespace-nowrap
          rounded-md bg-slate-900 px-2 py-1 text-xs text-white opacity-0 shadow-md transition-opacity
          group-hover:opacity-100 group-focus-within:opacity-100"
      >
        {label}
      </span>
    </span>
  );
}

export default Tooltip;
