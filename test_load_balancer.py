"""
python3.9 -m unittest test_load_balancer.py
"""

import unittest
import asyncio
# from concurrent.futures import ThreadPoolExecutor

from load_balancer import Account, LoadBalancer, RandomStrategy, RoundRobinStrategy


class TestLoadBalancer(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop()
        # self.executor = ThreadPoolExecutor(max_workers=10)

    def test_register_server(self):
        """Checks that the server registers successfully."""
        load_balancer = LoadBalancer()
        self.loop.run_until_complete(load_balancer.register_server("192.168.1.1"))
        self.assertIn("192.168.1.1", load_balancer.servers)

    def test_register_duplicate_server(self):
        """Checks that re-registering the server returns False."""
        load_balancer = LoadBalancer()
        self.loop.run_until_complete(load_balancer.register_server("192.168.1.1"))
        result = self.loop.run_until_complete(load_balancer.register_server("192.168.1.1"))
        self.assertFalse(result)

    def test_register_max_servers(self):
        """Checks that False is returned when attempting to register more than 10 servers."""
        load_balancer = LoadBalancer()
        for i in range(10):
            self.loop.run_until_complete(load_balancer.register_server(f"192.168.1.{i + 1}"))
        result = self.loop.run_until_complete(load_balancer.register_server("192.168.1.11"))
        self.assertFalse(result)

    def test_remove_server(self):
        """Checks that the server is being removed successfully."""
        load_balancer = LoadBalancer()
        self.loop.run_until_complete(load_balancer.register_server("192.168.1.1"))
        result = self.loop.run_until_complete(load_balancer.remove_server("192.168.1.1"))
        self.assertTrue(result)
        self.assertNotIn("192.168.1.1", load_balancer.servers)

    def test_remove_non_existent_server(self):
        """Checks that deleting a non-existent server returns False."""
        load_balancer = LoadBalancer()
        result = self.loop.run_until_complete(load_balancer.remove_server("192.168.1.1"))
        self.assertFalse(result)

    def test_round_robin_strategy(self):
        """Checks that servers are selected in a round-robin manner."""
        load_balancer = LoadBalancer()
        # Registering servers
        self.loop.run_until_complete(load_balancer.register_server("192.168.1.1"))
        self.loop.run_until_complete(load_balancer.register_server("192.168.1.2"))

        # We set up a new circular strategy and reset the index
        round_robin_strategy = RoundRobinStrategy()  # Create a new instance every time
        load_balancer.set_strategy(round_robin_strategy)

        # Reset strategy (if necessary)
        round_robin_strategy.reset()

        # We check the selection of servers in a circle
        server1 = self.loop.run_until_complete(load_balancer.get_server())
        server2 = self.loop.run_until_complete(load_balancer.get_server())

        self.assertEqual(server1, "192.168.1.1")
        self.assertEqual(server2, "192.168.1.2")

    def test_random_strategy(self):
        """Checks that servers are selected randomly."""
        load_balancer = LoadBalancer()
        self.loop.run_until_complete(load_balancer.register_server("192.168.1.1"))
        self.loop.run_until_complete(load_balancer.register_server("192.168.1.2"))
        load_balancer.set_strategy(RandomStrategy())

        # We run several elections to check that the servers are selected randomly
        selected_servers = [self.loop.run_until_complete(load_balancer.get_server()) for _ in range(10)]
        self.assertIn("192.168.1.1", selected_servers)
        self.assertIn("192.168.1.2", selected_servers)


class TestAccount(unittest.TestCase):
    def setUp(self):
        self.account1 = Account("Account1", 100.0)
        self.account2 = Account("Account2", 50.0)
        self.loop = asyncio.get_event_loop()

    async def transfer_wrapper(self, amount, target_account):
        """
        Used to facilitate parallel execution of a transfer between two accounts.
        This method wraps the transfer function call in an additional layer of control,
        to ensure that asynchronous tasks are executed correctly.
        """
        await self.account1.transfer(amount, target_account)

    def test_successful_transfer(self):
        """Checks successful transfer of funds between accounts."""
        self.loop.run_until_complete(self.transfer_wrapper(30.0, self.account2))
        self.assertEqual(self.account1.balance, 70.0)
        self.assertEqual(self.account2.balance, 80.0)

    def test_transfer_insufficient_funds(self):
        """Ensures that an exception is thrown if there are insufficient funds."""
        with self.assertRaises(ValueError) as context:
            self.loop.run_until_complete(self.transfer_wrapper(200.0, self.account2))
        self.assertEqual(str(context.exception), "Insufficient funds for transfer.")

    def test_transfer_negative_amount(self):
        """Checks that attempting to transfer a negative amount throws an exception."""
        with self.assertRaises(ValueError) as context:
            self.loop.run_until_complete(self.transfer_wrapper(-10.0, self.account2))
        self.assertEqual(str(context.exception), "The transfer amount must be positive.")


if __name__ == "__main__":
    unittest.main()
