package ex00;

public class BitOperator {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		short a=(short)0x55ff; //01010101 11111111
		short b=(short)0x00ff; //00000000 11111111
		
		//비트 논리 연산
		System.out.println("[비트 연산 결과]");
		// %c %d %f %s %b %04x(4자리의 16진수)
		System.out.printf("%04x\n",(short)(a&b)); //비트 AND 00000000 11111111
		System.out.printf("%04x\n",(short)(a|b)); //비트 OR  01010101 11111111
		System.out.printf("%04x\n",(short)(a^b)); //비트 XOR 01010101 00000000
		System.out.printf("%04x\n",(short)(~a)); //비트 NOT  10101010 00000000
		
		byte c= 20; //0x14 00000000 00010100
		byte d =-8; //0xf8 11111111 11111000 8 =(00000000 00001000) 
		// 비트 시프트 연산
		System.out.println("[시프트 연산 결과]");
		System.out.println(c<<2); //c를 2비트 왼쪽 시프트 00000000 01010000 
		System.out.println(c>>2); //c를 2비트 오른쪽 시프트, 0삽입 00000000 00000101
		System.out.println(d>>2); //d를 2비트 오른쪽 시프트, 1삽입 11111111 11111110
		System.out.printf("%x\n",(d>>>2)); // d를 2비트 오른쪽 시프트, 0삽입 논리적시프트 00111111 11111110
	}

}
