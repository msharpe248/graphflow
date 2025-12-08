import { useEffect } from 'react'
import { useSettingsStore } from '@/stores/settingsStore'
import { useChatStore } from '@/stores/chatStore'
import { useAgent } from '@/hooks/useRuntime'
import { isGraphChatEligible } from '@/types/chat'
import ChatLayout from '@/components/layout/ChatLayout'

function App() {
  const { checkConnection, runtime } = useSettingsStore()
  const { addGraph, selectGraph, createConversation, activeGraphs } = useChatStore()

  // Get agentId from URL parameters
  const urlParams = new URLSearchParams(window.location.search)
  const agentIdFromUrl = urlParams.get('agentId')

  // Fetch the agent if agentId is in URL
  const { data: agent } = useAgent(agentIdFromUrl)

  // Check connection on mount and periodically
  useEffect(() => {
    checkConnection()
    const interval = setInterval(checkConnection, 30000)
    return () => clearInterval(interval)
  }, [checkConnection])

  // Add agent from URL parameter when it's loaded
  useEffect(() => {
    if (agent && runtime.connected) {
      // Check if eligible
      if (!isGraphChatEligible(agent.graph_definition)) {
        console.warn('Agent from URL is not chat-eligible')
        return
      }

      // Check if already added
      const alreadyAdded = activeGraphs.some(g => g.agentId === agent.id)
      if (alreadyAdded) {
        selectGraph(agent.id)
        return
      }

      // Add the graph
      addGraph({
        agentId: agent.id,
        name: agent.name,
        description: agent.description,
        graphDefinition: agent.graph_definition,
      })

      // Select it and create a new conversation
      selectGraph(agent.id)
      createConversation(agent.id)

      // Clear the URL parameter to prevent re-adding on refresh
      const newUrl = window.location.pathname
      window.history.replaceState({}, '', newUrl)
    }
  }, [agent, runtime.connected, activeGraphs, addGraph, selectGraph, createConversation])

  return <ChatLayout />
}

export default App
