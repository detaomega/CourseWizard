import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";
import React from "react";

interface CourseSearchBarProps {
  searchQuery: string;
  setSearchQuery: (v: string) => void;
  handleSearch: () => void;
  isLoading: boolean;
}

const CourseSearchBar: React.FC<CourseSearchBarProps> = ({
  searchQuery,
  setSearchQuery,
  handleSearch,
  isLoading,
}) => (
  <Card className="bg-white/90 backdrop-blur-sm border-blue-200 shadow-lg">
    <CardHeader>
      <CardTitle className="text-gray-900 flex items-center gap-2">
        <Search className="w-5 h-5" />
        課程搜索
      </CardTitle>
      <CardDescription className="text-gray-600">
        告訴我們你想學什麼，例如：「我想修資安相關的課」
      </CardDescription>
    </CardHeader>
    <CardContent>
      <div className="flex gap-4">
        <Input
          placeholder="例如：我想修資安相關的課"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 border-blue-300 focus:border-blue-500 focus:ring-blue-500"
          onKeyPress={(e) => e.key === "Enter" && handleSearch()}
        />
        <Button
          onClick={handleSearch}
          disabled={isLoading || !searchQuery.trim()}
          className="bg-blue-600 hover:bg-blue-700 text-white px-8"
        >
          {isLoading ? "搜索中..." : "搜索課程"}
        </Button>
      </div>
    </CardContent>
  </Card>
);

export default CourseSearchBar;