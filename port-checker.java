import java.net.*;
import java.io.*;

/**
 * 端口可用性检查工具
 */
public class PortChecker {
    
    /**
     * 检查端口是否可用
     */
    public static boolean isPortAvailable(int port) {
        try (ServerSocket serverSocket = new ServerSocket(port)) {
            serverSocket.setReuseAddress(true);
            return true;
        } catch (IOException e) {
            return false;
        }
    }
    
    /**
     * 查找可用端口
     */
    public static int findAvailablePort(int startPort, int endPort) {
        for (int port = startPort; port <= endPort; port++) {
            if (isPortAvailable(port)) {
                return port;
            }
        }
        return -1; // 没有找到可用端口
    }
    
    /**
     * 从候选端口列表中找到第一个可用的
     */
    public static int findAvailablePort(int[] candidatePorts) {
        for (int port : candidatePorts) {
            if (isPortAvailable(port)) {
                return port;
            }
        }
        return -1;
    }
    
    public static void main(String[] args) {
        // 测试端口
        int[] testPorts = {8688, 25565, 25566, 30000, 3000, 2705};
        
        System.out.println("=== 端口可用性检查 ===");
        for (int port : testPorts) {
            boolean available = isPortAvailable(port);
            System.out.println("端口 " + port + ": " + (available ? "✅ 可用" : "❌ 被占用"));
        }
        
        System.out.println("\n=== 查找可用端口 ===");
        int availablePort = findAvailablePort(testPorts);
        if (availablePort != -1) {
            System.out.println("找到可用端口: " + availablePort);
        } else {
            System.out.println("没有找到可用端口！");
        }
    }
}
