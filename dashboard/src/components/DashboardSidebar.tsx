import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarFooter,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuSub,
  SidebarMenuSubItem,
  SidebarMenuSubButton,
  SidebarGroup,
  SidebarGroupContent,
} from '@/components/ui/sidebar';
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from '@/components/ui/collapsible';
import { LayoutDashboard, GitBranch, Activity, Settings, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * DashboardSidebar provides navigation for the Amelia dashboard.
 * Uses shadcn/ui Sidebar with collapsible sections.
 *
 * Features:
 * - SidebarProvider for state management (in parent layout)
 * - Cookie-based state persistence
 * - Mobile responsive with sheet drawer
 * - Keyboard navigation with focus-visible states
 */
export function DashboardSidebar() {
  return (
    <Sidebar className="border-r border-border">
      <SidebarHeader className="px-4 py-6">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-md bg-primary/20 flex items-center justify-center">
            <LayoutDashboard className="h-4 w-4 text-primary" />
          </div>
          <span className="font-heading text-lg font-bold tracking-wider">
            AMELIA
          </span>
        </div>
      </SidebarHeader>

      <SidebarContent className="px-2">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {/* Workflows section - collapsible */}
              <Collapsible defaultOpen className="group/collapsible">
                <SidebarMenuItem>
                  <CollapsibleTrigger asChild>
                    <SidebarMenuButton
                      className={cn(
                        'w-full justify-between',
                        'focus-visible:ring-ring/50 focus-visible:ring-[3px]'
                      )}
                    >
                      <span className="flex items-center gap-2">
                        <GitBranch className="h-4 w-4" />
                        Workflows
                      </span>
                      <ChevronDown className="h-4 w-4 transition-transform duration-200 group-data-[state=open]/collapsible:rotate-180" />
                    </SidebarMenuButton>
                  </CollapsibleTrigger>

                  <CollapsibleContent>
                    <SidebarMenuSub>
                      <SidebarMenuSubItem>
                        <SidebarMenuSubButton
                          className="focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                        >
                          Active
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                      <SidebarMenuSubItem>
                        <SidebarMenuSubButton
                          className="focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                        >
                          Completed
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                      <SidebarMenuSubItem>
                        <SidebarMenuSubButton
                          className="focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                        >
                          Failed
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                    </SidebarMenuSub>
                  </CollapsibleContent>
                </SidebarMenuItem>
              </Collapsible>

              {/* Activity */}
              <SidebarMenuItem>
                <SidebarMenuButton
                  className="focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                >
                  <Activity className="h-4 w-4" />
                  Activity
                </SidebarMenuButton>
              </SidebarMenuItem>

              {/* Settings */}
              <SidebarMenuItem>
                <SidebarMenuButton
                  className="focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                >
                  <Settings className="h-4 w-4" />
                  Settings
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="px-4 py-4 border-t border-border">
        <p className="text-xs text-muted-foreground">
          Amelia v1.0.0
        </p>
      </SidebarFooter>
    </Sidebar>
  );
}
