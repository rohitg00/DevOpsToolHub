import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { ThumbsUp } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Tool } from "@/lib/types";
import { useState, useEffect } from "react";

interface ToolPopularityProps {
  tool: Tool;
}

export function ToolPopularity({ tool }: ToolPopularityProps) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [hasVoted, setHasVoted] = useState(false);
  const [isCheckingVote, setIsCheckingVote] = useState(false);

  // Only check vote status when the button is hovered or focused
  const checkVoteStatus = async () => {
    if (isCheckingVote) return;
    setIsCheckingVote(true);
    
    try {
      const response = await fetch(`/api/tools/${encodeURIComponent(tool.name)}/upvote`, {
        method: 'HEAD',
        credentials: 'include',
      });
      setHasVoted(response.ok);
    } catch (error) {
      console.error('Error checking vote status:', error);
    } finally {
      setIsCheckingVote(false);
    }
  };

  const toggleVote = useMutation({
    mutationFn: async () => {
      const response = await fetch(`/api/tools/${encodeURIComponent(tool.name)}/upvote`, {
        method: 'POST',
        credentials: 'include',
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(error);
      }

      const result = await response.json();
      return result;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['/api/tools'] });
      setHasVoted(data.action === 'added');
      toast({
        title: "Success",
        description: data.action === 'added' ? "Thanks for your vote!" : "Vote removed",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => toggleVote.mutate()}
      onMouseEnter={checkVoteStatus}
      onFocus={checkVoteStatus}
      disabled={toggleVote.isPending}
      className={hasVoted ? "text-blue-500" : ""}
    >
      <ThumbsUp className={`w-4 h-4 mr-1 ${hasVoted ? "fill-current" : ""}`} />
      {tool.upvotes || 0}
    </Button>
  );
}
