import {
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

function Pagination({
  page,
  pages,
  total,
  onPageChange,
}) {
  return (
    <div className="pagination">
      <div className="pagination-summary">
        {total} alert{total === 1 ? "" : "s"}
      </div>

      <div className="pagination-controls">
        <button
          disabled={page <= 1}
          onClick={() =>
            onPageChange(page - 1)
          }
        >
          <ChevronLeft size={15} />
        </button>

        <span>
          Page {page} of {Math.max(pages, 1)}
        </span>

        <button
          disabled={
            pages === 0 ||
            page >= pages
          }
          onClick={() =>
            onPageChange(page + 1)
          }
        >
          <ChevronRight size={15} />
        </button>
      </div>
    </div>
  );
}

export default Pagination;
