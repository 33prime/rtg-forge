interface TagListProps {
  tags: string[];
  limit?: number;
}

export default function TagList({ tags, limit }: TagListProps) {
  const visible = limit ? tags.slice(0, limit) : tags;
  const remaining = limit ? tags.length - limit : 0;

  return (
    <div className="flex flex-wrap gap-1.5">
      {visible.map((tag) => (
        <span
          key={tag}
          className="inline-flex rounded-full bg-[#09090b] px-2 py-0.5 text-[11px] font-medium text-[#71717a]"
        >
          {tag}
        </span>
      ))}
      {remaining > 0 && (
        <span className="inline-flex rounded-full bg-[#09090b] px-2 py-0.5 text-[11px] font-medium text-[#71717a]">
          +{remaining}
        </span>
      )}
    </div>
  );
}
