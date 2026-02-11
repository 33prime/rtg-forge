import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { loadSkills, loadSkillDocs } from '../lib/data';
import SkillDetail from '../components/skills/SkillDetail';
import EmptyState from '../components/shared/EmptyState';

export default function SkillDetailPage() {
  const { category, name } = useParams<{ category: string; name: string }>();
  const navigate = useNavigate();

  const { data: skills, isLoading: skillsLoading } = useQuery({
    queryKey: ['skills'],
    queryFn: loadSkills,
  });

  const { data: docs } = useQuery({
    queryKey: ['skill-docs'],
    queryFn: loadSkillDocs,
  });

  if (skillsLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="text-[#71717a]">Loading skill...</div>
      </div>
    );
  }

  const skill = skills?.find(
    (s) => s.skill.category === category && s.skill.name === name
  );

  if (!skill) {
    return (
      <EmptyState
        title="Skill not found"
        message={`No skill named "${category}/${name}" was found.`}
        icon="search"
        action={{ label: 'Back to Skills', onClick: () => navigate('/skills') }}
      />
    );
  }

  const docKey = `${category}/${name}`;
  const skillDoc = docs?.[docKey];

  return <SkillDetail skill={skill} docs={skillDoc} />;
}
